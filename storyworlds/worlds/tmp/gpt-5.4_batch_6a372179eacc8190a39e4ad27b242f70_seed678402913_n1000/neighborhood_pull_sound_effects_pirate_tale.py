#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/neighborhood_pull_sound_effects_pirate_tale.py
==========================================================================

A standalone story world for a tiny pirate-style neighborhood adventure:
two children turn a wagon into a pirate ship, a piece of "treasure" gets stuck
somewhere awkward in the neighborhood, and a grown-up helps them pull it free
with the right tool.

The model is intentionally small and constraint-checked:

- A setting only supports certain snag places.
- A retrieval tool must be safe for that snag.
- The tool must reach far enough.
- The tool must also be able to catch the treasure's shape/material.

The story is always driven by state:
pretend play -> loss -> grounded warning -> sensible rescue -> changed ending.

The seed asked for:
- the word "neighborhood"
- the word "pull"
- sound effects
- pirate-tale style

Run it
------
    python storyworlds/worlds/gpt-5.4/neighborhood_pull_sound_effects_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/neighborhood_pull_sound_effects_pirate_tale.py --snag storm_drain
    python storyworlds/worlds/gpt-5.4/neighborhood_pull_sound_effects_pirate_tale.py --tool magnet_line --treasure pirate_flag
    python storyworlds/worlds/gpt-5.4/neighborhood_pull_sound_effects_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/neighborhood_pull_sound_effects_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/neighborhood_pull_sound_effects_pirate_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    scene: str
    route: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=lambda: {"neighborhood"})


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    shine: str
    pirate_use: str
    catch_points: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Snag:
    id: str
    label: str
    phrase: str
    danger: str
    why_not_hands: str
    depth: int
    sound: str
    close: str
    afford_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reach: int
    safe_for: set[str] = field(default_factory=set)
    works_on: set[str] = field(default_factory=set)
    action: str = ""
    pull_sound: str = ""
    qa_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_stuck_worry(world: World) -> list[str]:
    treasure = world.entities.get("treasure")
    snag = world.entities.get("snag")
    if treasure is None or snag is None:
        return []
    if treasure.meters["stuck"] < THRESHOLD:
        return []
    sig = ("stuck_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    snag.meters["risk"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__stuck__"]


def _r_unsafe_reach(world: World) -> list[str]:
    captain = next((k for k in world.kids() if k.role == "captain"), None)
    snag = world.entities.get("snag")
    if captain is None or snag is None:
        return []
    if captain.memes["reaching"] < THRESHOLD:
        return []
    sig = ("unsafe_reach",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.memes["fear"] += 1
    captain.memes["defiance"] += 1
    snag.meters["risk"] += 1
    return ["__reach__"]


def _r_recovered_relief(world: World) -> list[str]:
    treasure = world.entities.get("treasure")
    if treasure is None or treasure.meters["freed"] < THRESHOLD:
        return []
    sig = ("recovered_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treasure.meters["stuck"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["worry"] = 0.0
    if "snag" in world.entities:
        world.get("snag").meters["risk"] = 0.0
    return ["__recovered__"]


CAUSAL_RULES = [
    Rule(name="stuck_worry", tag="emotional", apply=_r_stuck_worry),
    Rule(name="unsafe_reach", tag="social", apply=_r_unsafe_reach),
    Rule(name="recovered_relief", tag="emotional", apply=_r_recovered_relief),
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
        for sentence in produced:
            world.say(sentence)
    return produced


def tool_fits(tool: Tool, treasure: Treasure, snag: Snag) -> bool:
    if snag.id not in tool.safe_for:
        return False
    if tool.reach < snag.depth:
        return False
    return bool(tool.works_on & treasure.catch_points)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for snag_id in sorted(setting.affords):
            snag = SNAGS[snag_id]
            for treasure_id, treasure in TREASURES.items():
                for tool_id, tool in TOOLS.items():
                    if tool_fits(tool, treasure, snag):
                        combos.append((setting_id, treasure_id, snag_id, tool_id))
    return combos


def explain_rejection(treasure: Treasure, snag: Snag, tool: Tool, setting: Optional[Setting] = None) -> str:
    if setting is not None and snag.id not in setting.affords:
        return (
            f"(No story: {snag.phrase} is not part of {setting.label}. "
            f"Pick a snag that belongs in that neighborhood route.)"
        )
    if snag.id not in tool.safe_for:
        return (
            f"(No story: {tool.label} is not a safe way to pull something from {snag.phrase}. "
            f"{snag.why_not_hands}"
        )
    if tool.reach < snag.depth:
        return (
            f"(No story: {tool.label} is too short to reach into {snag.phrase}. "
            f"It needs reach {snag.depth}, but this tool only reaches {tool.reach}.)"
        )
    if not (tool.works_on & treasure.catch_points):
        return (
            f"(No story: {tool.label} cannot catch {treasure.phrase} well enough to pull it free. "
            f"Choose a tool that works with its shape or material.)"
        )
    return "(No story: that combination is not reasonable.)"


def predict_risk(world: World) -> dict:
    sim = world.copy()
    captain = next((k for k in sim.kids() if k.role == "captain"), None)
    snag = sim.entities.get("snag")
    if captain is None or snag is None:
        return {"risk": 0.0, "fear": 0.0}
    captain.memes["reaching"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": snag.meters["risk"],
        "fear": captain.memes["fear"],
    }


def introduce(world: World, captain: Entity, mate: Entity, setting: Setting, treasure: Treasure) -> None:
    for kid in (captain, mate):
        kid.memes["joy"] += 1
        kid.memes["play"] += 1
    world.say(
        f"On a bright afternoon, {captain.id} and {mate.id} marched through the neighborhood, "
        f"certain that {setting.scene}. Their red wagon was a pirate ship, its rope was a salty line, "
        f"and {treasure.phrase} was the finest prize on deck."
    )
    world.say(
        f'Squeak-squeak went the wagon wheels. Clop-clop went their sneakers as they followed {setting.route}.'
    )
    world.say(
        f'"Captain {captain.id} and First Mate {mate.id}!" {captain.id} cried. '
        f'"Keep sharp eyes out for treasure!"'
    )


def admire_treasure(world: World, mate: Entity, treasure: Treasure) -> None:
    world.say(
        f"{mate.id} patted {treasure.phrase}. It {treasure.shine}, and to them it was {treasure.pirate_use}."
    )


def mishap(world: World, captain: Entity, treasure_ent: Entity, treasure: Treasure, snag_ent: Entity, snag: Snag) -> None:
    treasure_ent.meters["stuck"] += 1
    treasure_ent.attrs["where"] = snag.label
    propagate(world, narrate=False)
    world.say(
        f"Then the wagon bumped over a crack in the pavement -- bump! "
        f"{treasure.phrase.capitalize()} slid, tipped, and skittered away. "
        f'{snag.sound} It vanished into {snag.phrase}.'
    )
    if snag.id == "storm_drain":
        world.say(
            f"{captain.id} dropped to {captain.pronoun('possessive')} knees and stared through the metal slats. "
            f"The prize was still there, but now it was deep below."
        )
    else:
        world.say(
            f"There it hung, close enough to see, but badly snagged all the same."
        )


def rash_idea(world: World, captain: Entity, snag: Snag) -> None:
    captain.memes["boldness"] += 1
    world.say(
        f'"I can pull it out myself," {captain.id} said, leaning toward {snag.phrase}.'
    )
    world.say(f"{captain.pronoun().capitalize()} stretched out a hand.")


def warn(world: World, mate: Entity, captain: Entity, parent: Entity, snag: Snag) -> None:
    pred = predict_risk(world)
    mate.memes["caution"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_fear"] = pred["fear"]
    extra = " even before any scrape or splash happened" if pred["fear"] >= THRESHOLD else ""
    world.say(
        f'{mate.id} caught {captain.id}\'s sleeve. "{captain.id}, wait," {mate.pronoun()} said. '
        f'"{snag.why_not_hands}. Let\'s call {parent.label_word} instead."'
        f"{extra}"
    )


def reach_anyway(world: World, captain: Entity, snag: Snag) -> None:
    captain.memes["reaching"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Just a quick pull," {captain.id} whispered. But {snag.close}, and the place looked trickier up close than it had from the wagon.'
    )


def parent_arrives(world: World, parent: Entity) -> None:
    parent.memes["care"] += 1
    world.say(
        f'"Ahoy, what happened?" {parent.label_word.capitalize()} called, hurrying over when the children shouted for help.'
    )


def assess(world: World, parent: Entity, treasure: Treasure, snag: Snag, tool: Tool) -> None:
    world.say(
        f"{parent.label_word.capitalize()} saw {treasure.phrase} in {snag.phrase} and nodded. "
        f'"We do not reach into places like that with bare hands," {parent.pronoun()} said. '
        f'"We use the right thing to pull it free."'
    )
    world.say(
        f"From nearby, {parent.pronoun()} brought {tool.phrase}."
    )


def rescue(world: World, parent: Entity, tool_ent: Entity, treasure_ent: Entity, tool: Tool, treasure: Treasure, snag: Snag) -> None:
    tool_ent.meters["used"] += 1
    treasure_ent.meters["freed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} {tool.action}. "
        f"{tool.pull_sound} -- and out came {treasure.label} at last."
    )
    world.say(
        f"{parent.pronoun().capitalize()} set it safely back in the wagon, far from {snag.label}."
    )


def lesson(world: World, parent: Entity, captain: Entity, mate: Entity, tool: Tool, snag: Snag) -> None:
    for kid in (captain, mate):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} crouched beside them. "The brave thing is not grabbing first," '
        f'{parent.pronoun()} said softly. "The brave thing is stopping, noticing danger, and asking for help."'
    )
    world.say(
        f'"And using {tool.label}," {mate.id} said.'
    )
    world.say(
        f'"Right," {parent.label_word} smiled. "That is how we pull treasure away from {snag.label} safely."'
    )


def ending(world: World, captain: Entity, mate: Entity, setting: Setting, treasure: Treasure) -> None:
    for kid in (captain, mate):
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"Soon they were off again, rolling through the neighborhood with {treasure.label} tucked safely aboard."
    )
    world.say(
        f'Squeak-squeak went the wagon. Swish went the pirate flag tied to the handle. '
        f'{captain.id} gave the rope a careful pull, and this time everyone kept a watchful eye on the deck.'
    )
    world.say(
        f"By the end of the block, the little ship had crossed {setting.label} once more -- not just brave, but careful too."
    )


def tell(
    setting: Setting,
    treasure_cfg: Treasure,
    snag_cfg: Snag,
    tool_cfg: Tool,
    captain_name: str,
    captain_gender: str,
    mate_name: str,
    mate_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World(setting)
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        traits=["bold"],
    ))
    mate = world.add(Entity(
        id=mate_name,
        kind="character",
        type=mate_gender,
        role="mate",
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    treasure_ent = world.add(Entity(
        id="treasure",
        type="treasure",
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        attrs={"catch_points": sorted(treasure_cfg.catch_points)},
        tags=set(treasure_cfg.tags),
    ))
    snag_ent = world.add(Entity(
        id="snag",
        type="snag",
        label=snag_cfg.label,
        phrase=snag_cfg.phrase,
        attrs={"depth": snag_cfg.depth, "danger": snag_cfg.danger},
        tags=set(snag_cfg.tags),
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        attrs={"reach": tool_cfg.reach},
        tags=set(tool_cfg.tags),
    ))

    introduce(world, captain, mate, setting, treasure_cfg)
    admire_treasure(world, mate, treasure_cfg)

    world.para()
    mishap(world, captain, treasure_ent, treasure_cfg, snag_ent, snag_cfg)
    rash_idea(world, captain, snag_cfg)
    warn(world, mate, captain, parent, snag_cfg)
    reach_anyway(world, captain, snag_cfg)

    world.para()
    parent_arrives(world, parent)
    assess(world, parent, treasure_cfg, snag_cfg, tool_cfg)
    rescue(world, parent, tool_ent, treasure_ent, tool_cfg, treasure_cfg, snag_cfg)
    lesson(world, parent, captain, mate, tool_cfg, snag_cfg)

    world.para()
    ending(world, captain, mate, setting, treasure_cfg)

    world.facts.update(
        captain=captain,
        mate=mate,
        parent=parent,
        setting=setting,
        treasure_cfg=treasure_cfg,
        snag_cfg=snag_cfg,
        tool_cfg=tool_cfg,
        treasure=treasure_ent,
        snag=snag_ent,
        tool=tool_ent,
        recovered=treasure_ent.meters["freed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "maple_lane": Setting(
        id="maple_lane",
        label="Maple Lane",
        scene="the whole lane was a bright blue sea between picket fences",
        route="the shady sidewalk past mailboxes and little gardens",
        affords={"storm_drain", "rose_bush"},
        tags={"neighborhood"},
    ),
    "sunny_culdesac": Setting(
        id="sunny_culdesac",
        label="Sunny Circle",
        scene="the round street was a secret bay inside the neighborhood",
        route="the curved sidewalk around the quiet circle",
        affords={"rose_bush", "muddy_gutter"},
        tags={"neighborhood"},
    ),
    "brick_courtyard": Setting(
        id="brick_courtyard",
        label="Brick Court",
        scene="the neat little court was a harbor with brick waves underfoot",
        route="the short path between stoops and potted flowers",
        affords={"storm_drain", "muddy_gutter"},
        tags={"neighborhood"},
    ),
}

TREASURES = {
    "map_tube": Treasure(
        id="map_tube",
        label="the map tube",
        phrase="a striped map tube",
        shine="glimmered with a brass cap",
        pirate_use="the captain's secret map case",
        catch_points={"tube", "loop"},
        tags={"map", "pull"},
    ),
    "coin_tin": Treasure(
        id="coin_tin",
        label="the coin tin",
        phrase="a small tin of pirate coins",
        shine="clinked softly whenever it moved",
        pirate_use="a chest of gold pieces",
        catch_points={"metal", "ring"},
        tags={"metal", "coins", "pull"},
    ),
    "pirate_flag": Treasure(
        id="pirate_flag",
        label="the pirate flag",
        phrase="a tiny black pirate flag on a loop",
        shine="fluttered with a proud little snap",
        pirate_use="the ship's finest battle flag",
        catch_points={"loop", "cloth"},
        tags={"flag", "pull"},
    ),
}

SNAGS = {
    "storm_drain": Snag(
        id="storm_drain",
        label="the storm drain",
        phrase="the storm drain by the curb",
        danger="deep slats and dirty water below",
        why_not_hands="That drain is deep, grimy, and full of narrow metal gaps",
        depth=3,
        sound="Clang-clatter",
        close="the curb was slippery and the spaces between the bars looked pinchy",
        afford_text="beside the curb where rainwater runs",
        tags={"storm_drain", "call_adult"},
    ),
    "rose_bush": Snag(
        id="rose_bush",
        label="the rose bush",
        phrase="the prickly rose bush by a fence",
        danger="sharp thorns",
        why_not_hands="Those thorns can scratch and poke",
        depth=1,
        sound="Snick-snick",
        close="tiny thorns stuck out like hooked nails",
        afford_text="next to a fence where roses lean over the walk",
        tags={"thorns", "call_adult"},
    ),
    "muddy_gutter": Snag(
        id="muddy_gutter",
        label="the muddy gutter",
        phrase="the muddy gutter beside the sidewalk",
        danger="slick muck and yucky puddle water",
        why_not_hands="That gutter is slick and yucky, and you could slip your hand right into the muck",
        depth=2,
        sound="Splish-splosh",
        close="brown water wobbled around the edge and the mud looked slippery",
        afford_text="along the curb after water dries down",
        tags={"mud", "call_adult"},
    ),
}

TOOLS = {
    "grabber": Tool(
        id="grabber",
        label="the long grabber",
        phrase="a long grabber with a clicking mouth",
        reach=3,
        safe_for={"storm_drain", "rose_bush", "muddy_gutter"},
        works_on={"tube", "loop", "cloth", "ring", "metal"},
        action="clicked the jaws open, reached down slowly, and caught the treasure",
        pull_sound="Click-click ... tug ... zip",
        qa_text="used a long grabber to reach in and pull the treasure free",
        tags={"grabber", "tool"},
    ),
    "broom_hook": Tool(
        id="broom_hook",
        label="the broom handle with a string hook",
        phrase="a broom handle with a bent string hook tied to the end",
        reach=3,
        safe_for={"storm_drain", "muddy_gutter"},
        works_on={"loop", "ring", "tube"},
        action="lowered the hook with careful hands and lifted until the prize caught",
        pull_sound="Scrape ... tug ... plup",
        qa_text="used a hooked broom handle to snag the treasure and lift it out",
        tags={"hook", "tool"},
    ),
    "magnet_line": Tool(
        id="magnet_line",
        label="the magnet line",
        phrase="a string with a strong magnet tied at the end",
        reach=3,
        safe_for={"storm_drain", "muddy_gutter"},
        works_on={"metal"},
        action="let the magnet drop, waited for the tiny clink, and drew the line back up",
        pull_sound="Clink ... pull ... rattle",
        qa_text="used a magnet on a string to pull the metal treasure back up",
        tags={"magnet", "tool"},
    ),
    "garden_gloves": Tool(
        id="garden_gloves",
        label="the garden gloves",
        phrase="a pair of thick garden gloves",
        reach=1,
        safe_for={"rose_bush"},
        works_on={"cloth", "loop", "tube"},
        action="slipped on the gloves and gently eased the treasure around the thorns",
        pull_sound="Rustle ... tug ... pop",
        qa_text="used thick garden gloves to pull the treasure carefully away from the thorns",
        tags={"gloves", "tool"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["careful", "thoughtful", "steady", "wise", "watchful"]


@dataclass
class StoryParams:
    setting: str
    treasure: str
    snag: str
    tool: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="maple_lane",
        treasure="map_tube",
        snag="storm_drain",
        tool="grabber",
        captain="Tom",
        captain_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        setting="sunny_culdesac",
        treasure="pirate_flag",
        snag="rose_bush",
        tool="garden_gloves",
        captain="Mia",
        captain_gender="girl",
        mate="Ben",
        mate_gender="boy",
        parent="father",
        trait="steady",
    ),
    StoryParams(
        setting="brick_courtyard",
        treasure="coin_tin",
        snag="muddy_gutter",
        tool="magnet_line",
        captain="Max",
        captain_gender="boy",
        mate="Zoe",
        mate_gender="girl",
        parent="mother",
        trait="watchful",
    ),
    StoryParams(
        setting="brick_courtyard",
        treasure="map_tube",
        snag="muddy_gutter",
        tool="broom_hook",
        captain="Ava",
        captain_gender="girl",
        mate="Leo",
        mate_gender="boy",
        parent="father",
        trait="thoughtful",
    ),
]


KNOWLEDGE = {
    "neighborhood": [
        (
            "What is a neighborhood?",
            "A neighborhood is the part of town around your home, where nearby houses, sidewalks, and streets are all together."
        )
    ],
    "storm_drain": [
        (
            "What is a storm drain for?",
            "A storm drain is an opening by the curb that lets rainwater flow away. It is not a place for children to reach into."
        )
    ],
    "thorns": [
        (
            "Why can a rose bush hurt your hands?",
            "Rose bushes can have sharp thorns. Those thorns can poke and scratch skin."
        )
    ],
    "mud": [
        (
            "Why is a muddy gutter slippery?",
            "Mud and dirty water make the ground slick. A hand or foot can slide when it touches that slippery mess."
        )
    ],
    "call_adult": [
        (
            "What should a child do when something falls into a dangerous place?",
            "Stop, stay back, and call a grown-up for help. The safe choice is to let an adult use the right tool."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool with a little mouth at the end that can pinch and hold something far away."
        )
    ],
    "hook": [
        (
            "How can a hook help pull something out?",
            "A hook can catch a loop or ring. Then a grown-up can pull the object back carefully."
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet pulls on some kinds of metal. That makes it useful for lifting small metal things."
        )
    ],
    "gloves": [
        (
            "Why do thick gloves help near thorns?",
            "Thick gloves cover your skin and help protect your hands from scratches when a grown-up handles prickly plants."
        )
    ],
    "map": [
        (
            "What is a map for?",
            "A map helps you know where to go. Pirates in stories use maps to hunt for treasure."
        )
    ],
    "coins": [
        (
            "Why do coins clink?",
            "Coins are hard metal pieces. When they bump together, they make a little clinking sound."
        )
    ],
    "flag": [
        (
            "What does a flag do on a pretend ship?",
            "A flag shows who the ship belongs to. In pretend play, it helps the game feel real."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "neighborhood",
    "storm_drain",
    "thorns",
    "mud",
    "call_adult",
    "grabber",
    "hook",
    "magnet",
    "gloves",
    "map",
    "coins",
    "flag",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    treasure = f["treasure_cfg"]
    snag = f["snag_cfg"]
    tool = f["tool_cfg"]
    setting = f["setting"]
    return [
        (
            f'Write a short pirate-style story for a 3-to-5-year-old that includes the words '
            f'"neighborhood" and "pull", and uses sound effects while two children rescue pretend treasure.'
        ),
        (
            f"Tell a neighborhood pirate tale where {captain.id} and {mate.id} lose {treasure.phrase} in {snag.phrase}, "
            f"and a grown-up uses {tool.phrase} to pull it free safely."
        ),
        (
            f'Write a gentle adventure set on {setting.label} where a wagon becomes a pirate ship, '
            f'something goes wrong, and the ending shows the children playing more carefully than before.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    parent = f["parent"]
    setting = f["setting"]
    treasure = f["treasure_cfg"]
    snag = f["snag_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {captain.id} and {mate.id}, two children pretending to be pirates in their neighborhood, and {captain.id}'s {parent.label_word} who helps them."
        ),
        (
            "What were they pretending the wagon was?",
            f"They were pretending the wagon was a pirate ship. That game is what made {treasure.label} feel like real treasure."
        ),
        (
            f"Where did {treasure.label} get stuck?",
            f"It got stuck in {snag.phrase}. The children could still see it, but it was not safe to grab with bare hands."
        ),
        (
            f"Why did {mate.id} tell {captain.id} to stop?",
            f"{mate.id} knew {snag.why_not_hands.lower()}. Reaching in by hand could have led to a poke, pinch, or slippery mess."
        ),
        (
            f"How did the grown-up get {treasure.label} back?",
            f"{parent.label_word.capitalize()} {tool.qa_text}. That worked because the tool was right for both {snag.label} and the treasure itself."
        ),
        (
            "How did the story end?",
            f"The children went back to rolling through the neighborhood with the treasure safe in the wagon. The final image shows them still playing pirates, but more carefully than before."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"neighborhood"} | set(f["snag_cfg"].tags) | set(f["tool_cfg"].tags) | set(f["treasure_cfg"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_tool(Tool, Snag) :-
    tool(Tool), snag(Snag), safe_for(Tool, Snag).

reaches(Tool, Snag) :-
    tool(Tool), snag(Snag), tool_reach(Tool, Reach), snag_depth(Snag, Need), Reach >= Need.

catches(Tool, Treasure) :-
    tool(Tool), treasure(Treasure), tool_works_on(Tool, Point), catch_point(Treasure, Point).

valid(Setting, Treasure, Snag, Tool) :-
    setting(Setting), treasure(Treasure), snag(Snag), tool(Tool),
    affords(Setting, Snag),
    safe_tool(Tool, Snag),
    reaches(Tool, Snag),
    catches(Tool, Treasure).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for snag_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, snag_id))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        for point in sorted(treasure.catch_points):
            lines.append(asp.fact("catch_point", treasure_id, point))
    for snag_id, snag in SNAGS.items():
        lines.append(asp.fact("snag", snag_id))
        lines.append(asp.fact("snag_depth", snag_id, snag.depth))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_reach", tool_id, tool.reach))
        for snag_id in sorted(tool.safe_for):
            lines.append(asp.fact("safe_for", tool_id, snag_id))
        for point in sorted(tool.works_on):
            lines.append(asp.fact("tool_works_on", tool_id, point))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _check_param_keys(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Invalid treasure: {params.treasure})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Invalid snag: {params.snag})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Invalid parent: {params.parent})")


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

    smoke_cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"SMOKE SETUP FAIL at seed {seed}")
            break

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "neighborhood" not in sample.story.lower():
                raise StoryError("story missing required seed word 'neighborhood'")
            if "pull" not in sample.story.lower():
                raise StoryError("story missing required seed word 'pull'")
            if sample.world is None:
                raise StoryError("missing world")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL case {idx}: {err}")
            break
    else:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a neighborhood pirate wagon, lost treasure, and the right way to pull it back."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.snag:
        setting = SETTINGS[args.setting]
        snag = SNAGS[args.snag]
        if snag.id not in setting.affords:
            treasure = TREASURES[args.treasure] if args.treasure else next(iter(TREASURES.values()))
            tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
            raise StoryError(explain_rejection(treasure, snag, tool, setting))

    if args.treasure and args.snag and args.tool:
        treasure = TREASURES[args.treasure]
        snag = SNAGS[args.snag]
        tool = TOOLS[args.tool]
        setting = SETTINGS[args.setting] if args.setting else None
        if not tool_fits(tool, treasure, snag):
            raise StoryError(explain_rejection(treasure, snag, tool, setting))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.treasure is None or combo[1] == args.treasure)
        and (args.snag is None or combo[2] == args.snag)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, treasure_id, snag_id, tool_id = rng.choice(sorted(combos))
    captain, captain_gender = _pick_kid(rng)
    mate, mate_gender = _pick_kid(rng, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        treasure=treasure_id,
        snag=snag_id,
        tool=tool_id,
        captain=captain,
        captain_gender=captain_gender,
        mate=mate,
        mate_gender=mate_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    _check_param_keys(params)
    setting = SETTINGS[params.setting]
    treasure = TREASURES[params.treasure]
    snag = SNAGS[params.snag]
    tool = TOOLS[params.tool]
    if snag.id not in setting.affords or not tool_fits(tool, treasure, snag):
        raise StoryError(explain_rejection(treasure, snag, tool, setting))

    world = tell(
        setting=setting,
        treasure_cfg=treasure,
        snag_cfg=snag,
        tool_cfg=tool,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, treasure, snag, tool) combos:\n")
        for setting_id, treasure_id, snag_id, tool_id in combos:
            print(f"  {setting_id:15} {treasure_id:12} {snag_id:13} {tool_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain} & {p.mate}: {p.treasure} at {p.snag} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
