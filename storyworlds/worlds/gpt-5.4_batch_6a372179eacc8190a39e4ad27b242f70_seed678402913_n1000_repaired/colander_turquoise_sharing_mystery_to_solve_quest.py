#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/colander_turquoise_sharing_mystery_to_solve_quest.py
================================================================================

A standalone storyworld for a tiny space-adventure domain built from the seed
words "colander" and "turquoise" plus the features Sharing, Mystery to Solve,
and Quest.

Premise
-------
Two young explorers on a small space outpost lose an important turquoise object.
A trail of clues points to a hiding place. They have one retrieval tool, and
the mystery is only solved when they share jobs instead of grabbing for the same
thing. The quest ends when the lost object is recovered and the place glows
bright again.

Reasonableness gate
-------------------
Not every object, hiding place, and tool fit together. A colander can scoop a
small object from a pebble tray or bubble pool, but it is no help in a vent.
A magnet only works on metal objects. Tongs can reach into a vent but cannot
sensibly sift pebbles. The world refuses invalid combinations.

Run it
------
    python storyworlds/worlds/gpt-5.4/colander_turquoise_sharing_mystery_to_solve_quest.py
    python storyworlds/worlds/gpt-5.4/colander_turquoise_sharing_mystery_to_solve_quest.py --tool colander
    python storyworlds/worlds/gpt-5.4/colander_turquoise_sharing_mystery_to_solve_quest.py --hiding vent
    python storyworlds/worlds/gpt-5.4/colander_turquoise_sharing_mystery_to_solve_quest.py --all
    python storyworlds/worlds/gpt-5.4/colander_turquoise_sharing_mystery_to_solve_quest.py --verify
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
    traits: list[str] = field(default_factory=list)
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    quest_goal: str
    afford_hiding: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    material: str
    purpose: str
    color: str = "turquoise"
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    clue: str
    trail: str
    search_line: str
    found_line: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolDef:
    id: str
    label: str
    phrase: str
    action: str
    supports: set[str] = field(default_factory=set)
    materials: set[str] = field(default_factory=set)
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "partner"}]

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


def _r_missing_makes_mystery(world: World) -> list[str]:
    beacon = world.get("lost")
    if beacon.meters["missing"] < THRESHOLD:
        return []
    sig = ("mystery", "lost")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    station = world.get("station")
    station.meters["mystery"] += 1
    for kid in world.kids():
        kid.memes["curiosity"] += 1
    return ["__mystery__"]


def _r_shared_tool_builds_teamwork(world: World) -> list[str]:
    for kid in world.kids():
        if kid.memes["shared"] < THRESHOLD:
            return []
    sig = ("teamwork", "shared")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["teamwork"] += 1
        kid.memes["worry"] = 0.0
    world.get("station").memes["hope"] += 1
    return ["__teamwork__"]


def _r_found_finishes_quest(world: World) -> list[str]:
    lost = world.get("lost")
    if lost.meters["found"] < THRESHOLD:
        return []
    sig = ("quest", "done")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    station = world.get("station")
    station.meters["quest_done"] += 1
    station.meters["dark"] = 0.0
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    return ["__quest__"]


CAUSAL_RULES = [
    Rule(name="missing_makes_mystery", tag="social", apply=_r_missing_makes_mystery),
    Rule(name="shared_tool_builds_teamwork", tag="social", apply=_r_shared_tool_builds_teamwork),
    Rule(name="found_finishes_quest", tag="physical", apply=_r_found_finishes_quest),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "moon_market": Setting(
        id="moon_market",
        place="the little moon market",
        sky="Above the glass dome, the stars looked close enough to tap.",
        quest_goal="light the snack rocket sign before the market blinked shut",
        afford_hiding={"pebbles", "vent"},
        tags={"space", "market"},
    ),
    "comet_garden": Setting(
        id="comet_garden",
        place="the comet garden dome",
        sky="Outside the clear roof, slow comets painted pale tails across the dark.",
        quest_goal="wake the singing seed-bed before the evening mist rolled in",
        afford_hiding={"pebbles", "bubble_pool"},
        tags={"space", "garden"},
    ),
    "star_dock": Setting(
        id="star_dock",
        place="the star dock",
        sky="Beyond the rails, ships blinked like sleepy fireflies in the black.",
        quest_goal="turn the tiny guide beacon back on before the mail shuttle arrived",
        afford_hiding={"vent", "bubble_pool"},
        tags={"space", "dock"},
    ),
}

LOST_THINGS = {
    "beacon_bolt": LostThing(
        id="beacon_bolt",
        label="turquoise beacon bolt",
        phrase="a turquoise beacon bolt",
        material="metal",
        purpose="fit into the little beacon and wake its gentle light",
        tags={"turquoise", "metal", "beacon"},
    ),
    "star_marble": LostThing(
        id="star_marble",
        label="turquoise star marble",
        phrase="a turquoise star marble",
        material="stone",
        purpose="roll into the map reader and make the path sparkle",
        tags={"turquoise", "marble"},
    ),
    "shell_key": LostThing(
        id="shell_key",
        label="turquoise shell key",
        phrase="a turquoise shell key",
        material="shell",
        purpose="open the round song box that told the way home",
        tags={"turquoise", "key"},
    ),
}

HIDING_PLACES = {
    "pebbles": HidingPlace(
        id="pebbles",
        label="pebble tray",
        phrase="a tray of silver pebbles by the wall",
        clue="a small round trail in the dust led to the pebble tray",
        trail="The pebbles had one tiny groove through them, as if something had rolled there.",
        search_line="They hurried to the pebble tray and listened for a faint clink under the stones.",
        found_line="At last the missing thing rattled softly in the scoop.",
        needs={"scoop"},
        tags={"pebbles"},
    ),
    "vent": HidingPlace(
        id="vent",
        label="vent",
        phrase="the warm floor vent under the map table",
        clue="a thin turquoise glimmer winked through the vent slots",
        trail="A tiny glow slipped between the silver bars and vanished below.",
        search_line="They knelt by the vent and peered into its narrow dark.",
        found_line="The missing thing clicked against the metal bars and came free.",
        needs={"reach"},
        tags={"vent"},
    ),
    "bubble_pool": HidingPlace(
        id="bubble_pool",
        label="bubble pool",
        phrase="the bubbling moon-water pool",
        clue="three turquoise bubbles popped near the edge of the pool",
        trail="The water burbled once, and a flash of blue-green light winked below.",
        search_line="They tiptoed to the bubble pool and watched the rings widen.",
        found_line="The missing thing shone up from the watery bubbles and slid into the scoop.",
        needs={"scoop"},
        tags={"water"},
    ),
}

TOOLS = {
    "colander": ToolDef(
        id="colander",
        label="colander",
        phrase="a shiny kitchen colander from the galley",
        action="used the colander like a moon-scoop",
        supports={"pebbles", "bubble_pool"},
        materials={"metal", "stone", "shell"},
        tags={"colander", "sharing"},
    ),
    "grabber": ToolDef(
        id="grabber",
        label="grabber claw",
        phrase="a long grabber claw from the repair shelf",
        action="reached in with the grabber claw",
        supports={"vent"},
        materials={"metal", "stone", "shell"},
        tags={"tool", "sharing"},
    ),
    "magnet": ToolDef(
        id="magnet",
        label="magnet wand",
        phrase="a humming magnet wand",
        action="lowered the magnet wand carefully",
        supports={"vent", "bubble_pool"},
        materials={"metal"},
        tags={"magnet", "sharing"},
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Zuri", "Nova", "Ivy", "Aya"]
BOY_NAMES = ["Leo", "Milo", "Orin", "Tao", "Nico", "Eli"]
TRAITS = ["brave", "careful", "curious", "kind", "steady", "quick-thinking"]


def compatible(setting_id: str, hiding_id: str, item_id: str, tool_id: str) -> bool:
    if setting_id not in SETTINGS or hiding_id not in HIDING_PLACES or item_id not in LOST_THINGS or tool_id not in TOOLS:
        return False
    setting = SETTINGS[setting_id]
    hiding = HIDING_PLACES[hiding_id]
    item = LOST_THINGS[item_id]
    tool = TOOLS[tool_id]
    if hiding.id not in setting.afford_hiding:
        return False
    if hiding.id not in tool.supports:
        return False
    if item.material not in tool.materials:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id in LOST_THINGS:
            for hiding_id in HIDING_PLACES:
                for tool_id in TOOLS:
                    if compatible(setting_id, hiding_id, item_id, tool_id):
                        out.append((setting_id, item_id, hiding_id, tool_id))
    return out


def predict_success(world: World, hiding_id: str, tool_id: str, item_id: str) -> dict:
    sim = world.copy()
    ok = compatible(sim.setting.id, hiding_id, item_id, tool_id)
    if ok:
        sim.get("lost").meters["found"] += 1
        sim.get("lost").meters["missing"] = 0.0
        propagate(sim, narrate=False)
    return {
        "works": ok,
        "quest_done": sim.get("station").meters["quest_done"] >= THRESHOLD,
    }


def setup_scene(world: World, captain: Entity, partner: Entity, parent: Entity, item: LostThing) -> None:
    station = world.get("station")
    station.meters["dark"] += 1
    world.say(
        f"{captain.id} and {partner.id} were tiny space explorers helping at {world.setting.place}. "
        f"{world.setting.sky}"
    )
    world.say(
        f"That evening they had one important quest: {world.setting.quest_goal}. "
        f"To do that, they needed {item.phrase} to {item.purpose}."
    )
    world.say(
        f"{parent.label_word.capitalize()} set the last crate down and smiled. "
        f'"Guard that little piece for me," {parent.pronoun()} said. "It is small, but it matters."'
    )


def lose_item(world: World, captain: Entity, partner: Entity, item: LostThing, hiding: HidingPlace) -> None:
    lost = world.get("lost")
    lost.meters["missing"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {captain.id} lifted the tiny part to carry it across the room, it slipped, bounced once, and disappeared. "
        f"The room felt suddenly dimmer."
    )
    world.say(
        f'"The {item.label} is gone," {partner.id} whispered. {hiding.clue}.'
    )


def inspect_clue(world: World, captain: Entity, partner: Entity, hiding: HidingPlace) -> None:
    world.say(
        f"{captain.id} crouched low. {hiding.trail} "
        f"{partner.id} pressed close beside {captain.pronoun('object')}, studying every sparkle."
    )
    for kid in world.kids():
        kid.memes["curiosity"] += 1
    world.facts["clue_seen"] = True


def grab_same_tool(world: World, captain: Entity, partner: Entity, tool: ToolDef) -> None:
    captain.memes["possessive"] += 1
    partner.memes["possessive"] += 1
    captain.memes["worry"] += 1
    partner.memes["worry"] += 1
    world.say(
        f"On the supply shelf they found {tool.phrase}. "
        f"Both children reached for it at the same time."
    )
    world.say(
        f'"I need it," said {captain.id}. '
        f'"So do I," said {partner.id}. For one blink, the quest stopped right there.'
    )


def learn_to_share(world: World, captain: Entity, partner: Entity, parent: Entity, tool: ToolDef, hiding: HidingPlace, item: LostThing) -> None:
    pred = predict_success(world, hiding.id, tool.id, item.id)
    if not pred["works"]:
        raise StoryError("(Internal error: sharing beat called with an invalid tool for this mystery.)")
    captain.memes["shared"] += 1
    partner.memes["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} knelt beside them. "
        f'"A good crew shares jobs," {parent.pronoun()} said. '
        f'"One of you can guide the search, and one can use the tool. Then you switch if you need to."'
    )
    world.say(
        f"{captain.id} took a breath and nodded. {partner.id} nodded too. "
        f"They were still excited, but now they looked like a team."
    )


def search_together(world: World, captain: Entity, partner: Entity, tool: ToolDef, hiding: HidingPlace) -> None:
    world.say(
        f"{hiding.search_line} {captain.id} pointed to the best spot while {partner.id} {tool.action}."
    )
    if tool.id == "colander":
        world.say(
            f"The little holes let dust and water slip away while anything important stayed behind."
        )
    elif tool.id == "magnet":
        world.say(
            f"The wand gave a tiny hum, listening for hidden metal."
        )
    else:
        world.say(
            f"The claw moved slowly, careful not to push the treasure farther in."
        )


def recover_item(world: World, captain: Entity, partner: Entity, item: LostThing, hiding: HidingPlace, tool: ToolDef) -> None:
    lost = world.get("lost")
    lost.meters["found"] += 1
    lost.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Then {hiding.found_line} "
        f'"There it is!" shouted {partner.id}. {captain.id} held out both hands, and together they lifted out the {item.label}.'
    )
    world.say(
        f"It flashed turquoise in the soft station light, and all the worried quiet seemed to melt."
    )


def finish_quest(world: World, captain: Entity, partner: Entity, parent: Entity, item: LostThing) -> None:
    world.say(
        f"{captain.id} passed the {item.label} to {partner.id}, and {partner.pronoun()} passed it back so they could fit it in together. "
        f"That made {parent.label_word} smile even before the machine woke."
    )
    if item.id == "beacon_bolt":
        ending = "A tiny beacon blinked on and painted a turquoise star on the wall."
    elif item.id == "star_marble":
        ending = "The map reader purred, and a ribbon of turquoise light curled across its screen."
    else:
        ending = "The round song box chimed, and a turquoise ring of light glowed around its lid."
    world.say(
        f'Soon the quest was done. {ending} '
        f'{captain.id} and {partner.id} bumped shoulders and laughed, proud that sharing had solved the mystery.'
    )


def tell(
    setting: Setting,
    item: LostThing,
    hiding: HidingPlace,
    tool: ToolDef,
    captain_name: str = "Luna",
    captain_gender: str = "girl",
    partner_name: str = "Leo",
    partner_gender: str = "boy",
    parent_type: str = "mother",
    captain_trait: str = "brave",
    partner_trait: str = "careful",
) -> World:
    if not compatible(setting.id, hiding.id, item.id, tool.id):
        raise StoryError(explain_rejection(setting, item, hiding, tool))

    world = World(setting)
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        traits=[captain_trait],
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=[partner_trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    station = world.add(Entity(
        id="station",
        kind="thing",
        type="station",
        label=setting.place,
    ))
    lost = world.add(Entity(
        id="lost",
        kind="thing",
        type="part",
        label=item.label,
        phrase=item.phrase,
        attrs={"material": item.material, "purpose": item.purpose, "color": item.color},
        tags=set(item.tags),
    ))

    setup_scene(world, captain, partner, parent, item)
    world.para()
    lose_item(world, captain, partner, item, hiding)
    inspect_clue(world, captain, partner, hiding)
    world.para()
    grab_same_tool(world, captain, partner, tool)
    learn_to_share(world, captain, partner, parent, tool, hiding, item)
    world.para()
    search_together(world, captain, partner, tool, hiding)
    recover_item(world, captain, partner, item, hiding, tool)
    world.para()
    finish_quest(world, captain, partner, parent, item)

    world.facts.update(
        captain=captain,
        partner=partner,
        parent=parent,
        setting=setting,
        item_cfg=item,
        hiding=hiding,
        tool=tool,
        shared=all(kid.memes["shared"] >= THRESHOLD for kid in world.kids()),
        mystery=station.meters["mystery"] >= THRESHOLD,
        found=lost.meters["found"] >= THRESHOLD,
        quest_done=station.meters["quest_done"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "colander": [
        (
            "What is a colander?",
            "A colander is a bowl with lots of little holes in it. People use it to let water or tiny bits fall through while bigger things stay inside.",
        )
    ],
    "turquoise": [
        (
            "What color is turquoise?",
            "Turquoise is a blue-green color. It can look a little like bright sea water or a shiny gem.",
        )
    ],
    "sharing": [
        (
            "Why does sharing help on a team?",
            "Sharing helps because two people can each do part of a job. When teammates take turns and help each other, hard problems get easier.",
        )
    ],
    "mystery": [
        (
            "What is a mystery to solve?",
            "A mystery is something you do not know yet, like where an object went. You solve it by looking for clues and thinking carefully.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is an important job or journey with a goal at the end. In stories, a quest often means staying brave and solving problems along the way.",
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet can pull some kinds of metal toward it. That makes it useful for finding or lifting small metal things.",
        )
    ],
    "vent": [
        (
            "What is a vent?",
            "A vent is an opening that lets air move in or out. Small things can sometimes slip near the bars, so grown-ups use careful tools to reach them.",
        )
    ],
    "water": [
        (
            "Why do holes in a scoop help in water?",
            "The holes let the water run back out. That way the thing you want can stay in the scoop while the water drips away.",
        )
    ],
    "pebbles": [
        (
            "What are pebbles?",
            "Pebbles are small smooth stones. You can sift through them slowly to look for something hidden.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    partner = f["partner"]
    item = f["item_cfg"]
    hiding = f["hiding"]
    tool = f["tool"]
    return [
        'Write a short space-adventure story for a 3-to-5-year-old that includes the words "colander" and "turquoise", plus a mystery to solve, a quest, and sharing.',
        f"Tell a gentle story where {captain.id} and {partner.id} lose {item.phrase}, follow a clue to {hiding.phrase}, and must share {tool.phrase} to finish their quest.",
        f"Write a child-facing story with a small missing object, clear clues, teamwork, and a bright ending that proves the mystery was solved.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two young space girls"
    if a.type == "boy" and b.type == "boy":
        return "two young space boys"
    return "two young space explorers"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    partner = f["partner"]
    parent = f["parent"]
    item = f["item_cfg"]
    hiding = f["hiding"]
    tool = f["tool"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(captain, partner)}, {captain.id} and {partner.id}. They were helping at {setting.place} while {captain.id}'s {parent.label_word} watched over the quest.",
        ),
        (
            "What was the children's quest?",
            f"They needed to find {item.phrase} so it could {item.purpose}. Without it, the special machine stayed dark and the quest could not be finished.",
        ),
        (
            "What made the story a mystery?",
            f"The {item.label} slipped away and nobody knew where it had gone. The children had to follow a clue and think carefully to discover its hiding place.",
        ),
        (
            f"What clue told them where to look?",
            f"They saw that {hiding.clue}. That clue pointed them toward {hiding.phrase} and gave their search a clear direction.",
        ),
        (
            f"Why did {captain.id} and {partner.id} need to share?",
            f"They had only one useful tool, so grabbing at it stopped the quest for a moment. When they shared jobs instead, one child could guide the search while the other used the tool.",
        ),
        (
            f"How did they find the {item.label}?",
            f"They went to {hiding.phrase} and used {tool.phrase}. The tool matched the hiding place, so it could reach or scoop the missing thing safely.",
        ),
        (
            "How did the story end?",
            f"They solved the mystery, finished the quest, and the machine lit up with turquoise light. The bright ending showed that sharing had changed the problem into success.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"sharing", "mystery", "quest", "turquoise"}
    tool = f["tool"]
    hiding = f["hiding"]
    if tool.id == "colander":
        tags.add("colander")
        if hiding.id == "bubble_pool":
            tags.add("water")
    if tool.id == "magnet":
        tags.add("magnet")
    if hiding.id == "vent":
        tags.add("vent")
    if hiding.id == "pebbles":
        tags.add("pebbles")
    out: list[tuple[str, str]] = []
    order = ["colander", "turquoise", "sharing", "mystery", "quest", "magnet", "vent", "water", "pebbles"]
    for tag in order:
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    setting: str
    item: str
    hiding: str
    tool: str
    captain_name: str
    captain_gender: str
    partner_name: str
    partner_gender: str
    parent: str
    captain_trait: str
    partner_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="comet_garden",
        item="star_marble",
        hiding="pebbles",
        tool="colander",
        captain_name="Luna",
        captain_gender="girl",
        partner_name="Milo",
        partner_gender="boy",
        parent="mother",
        captain_trait="curious",
        partner_trait="steady",
    ),
    StoryParams(
        setting="star_dock",
        item="beacon_bolt",
        hiding="vent",
        tool="magnet",
        captain_name="Nova",
        captain_gender="girl",
        partner_name="Tao",
        partner_gender="boy",
        parent="father",
        captain_trait="brave",
        partner_trait="careful",
    ),
    StoryParams(
        setting="moon_market",
        item="shell_key",
        hiding="pebbles",
        tool="colander",
        captain_name="Aya",
        captain_gender="girl",
        partner_name="Leo",
        partner_gender="boy",
        parent="mother",
        captain_trait="kind",
        partner_trait="quick-thinking",
    ),
    StoryParams(
        setting="star_dock",
        item="beacon_bolt",
        hiding="bubble_pool",
        tool="colander",
        captain_name="Eli",
        captain_gender="boy",
        partner_name="Mira",
        partner_gender="girl",
        parent="father",
        captain_trait="steady",
        partner_trait="curious",
    ),
    StoryParams(
        setting="moon_market",
        item="star_marble",
        hiding="vent",
        tool="grabber",
        captain_name="Nico",
        captain_gender="boy",
        partner_name="Zuri",
        partner_gender="girl",
        parent="mother",
        captain_trait="brave",
        partner_trait="kind",
    ),
]


def explain_rejection(setting: Setting, item: LostThing, hiding: HidingPlace, tool: ToolDef) -> str:
    if hiding.id not in setting.afford_hiding:
        return (
            f"(No story: {setting.place} has no {hiding.label} to hide {item.phrase} in. "
            f"Pick a hiding place that belongs in this setting.)"
        )
    if hiding.id not in tool.supports:
        return (
            f"(No story: {tool.label} is not a sensible way to search {hiding.phrase}. "
            f"Choose a tool that can really reach or scoop there.)"
        )
    if item.material not in tool.materials:
        return (
            f"(No story: {tool.label} does not work on a {item.material} object like {item.phrase}. "
            f"Choose a tool that matches the lost item's material.)"
        )
    return "(No story: this mystery setup is not reasonable.)"


ASP_RULES = r"""
valid(S, I, H, T) :- setting(S), item(I), hiding(H), tool(T),
                     affords(S, H), supports(T, H), material(I, M), works_on(T, M).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.afford_hiding):
            lines.append(asp.fact("affords", sid, hid))
    for iid, item in LOST_THINGS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("material", iid, item.material))
    for hid in HIDING_PLACES:
        lines.append(asp.fact("hiding", hid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for hid in sorted(tool.supports):
            lines.append(asp.fact("supports", tid, hid))
        for mat in sorted(tool.materials):
            lines.append(asp.fact("works_on", tid, mat))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "turquoise" not in sample.story or "colander" not in sample.story and sample.params.tool == "colander":
            raise StoryError("(Smoke test failed: generated story missing expected content.)")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a shared tool, a missing turquoise part, and a little space quest."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=LOST_THINGS)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.hiding and args.tool:
        if not compatible(args.setting, args.hiding, args.item, args.tool):
            raise StoryError(explain_rejection(SETTINGS[args.setting], LOST_THINGS[args.item], HIDING_PLACES[args.hiding], TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.hiding is None or combo[2] == args.hiding)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, hiding_id, tool_id = rng.choice(sorted(combos))
    captain_gender = rng.choice(["girl", "boy"])
    partner_gender = rng.choice(["girl", "boy"])
    captain_name = _pick_name(rng, captain_gender)
    partner_name = _pick_name(rng, partner_gender, avoid=captain_name)
    parent_type = args.parent or rng.choice(["mother", "father"])
    captain_trait = rng.choice(TRAITS)
    partner_trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        hiding=hiding_id,
        tool=tool_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        parent=parent_type,
        captain_trait=captain_trait,
        partner_trait=partner_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in LOST_THINGS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if not compatible(params.setting, params.hiding, params.item, params.tool):
        raise StoryError(
            explain_rejection(
                SETTINGS[params.setting],
                LOST_THINGS[params.item],
                HIDING_PLACES[params.hiding],
                TOOLS[params.tool],
            )
        )
    world = tell(
        setting=SETTINGS[params.setting],
        item=LOST_THINGS[params.item],
        hiding=HIDING_PLACES[params.hiding],
        tool=TOOLS[params.tool],
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        parent_type=params.parent,
        captain_trait=params.captain_trait,
        partner_trait=params.partner_trait,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, hiding, tool) combos:\n")
        for setting_id, item_id, hiding_id, tool_id in combos:
            print(f"  {setting_id:12} {item_id:12} {hiding_id:11} {tool_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain_name} & {p.partner_name}: {p.item} in {p.hiding} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
