#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/solve_sole_imprison_reconciliation_space_adventure.py
=================================================================================

A standalone story world for a small, child-facing **space adventure about
reconciliation**.

Seed words required by the brief:
- solve
- sole
- imprison

Premise
-------
Two young space explorers are in the middle of a prickly argument when they find
a tiny alien trapped by a safety system. The trapped creature is not bad; the
system only made a fearful mistake. To free it, the children must calm down,
reconcile, and use the right tool for the right kind of barrier. The ending image
proves what changed: they stop pulling apart and work side by side.

Coverage constraint
-------------------
This world prefers fewer strong variants over many weak ones. The central
common-sense gate is:

- each prison type requires a compatible way to open or disable it;
- each location only plausibly supports certain prison types;
- the chosen tool must genuinely work on that prison;
- if the children do not reconcile, they may still *try*, but they cannot solve
  the problem because the needed action requires coordinated help.

The inline ASP twin mirrors that gate and the outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/solve_sole_imprison_reconciliation_space_adventure.py
    python storyworlds/worlds/gpt-5.4/solve_sole_imprison_reconciliation_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/solve_sole_imprison_reconciliation_space_adventure.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/solve_sole_imprison_reconciliation_space_adventure.py --qa
    python storyworlds/worlds/gpt-5.4/solve_sole_imprison_reconciliation_space_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/solve_sole_imprison_reconciliation_space_adventure.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        neuter = {"alien", "robot", "creature", "sprite"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neuter:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Locale:
    id: str
    place: str
    vehicle: str
    sky: str
    mission: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prison:
    id: str
    label: str
    phrase: str
    lock_type: str
    opener: str
    fear_reason: str
    allowed_locales: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    works_on: set[str] = field(default_factory=set)
    method: str = ""
    fail: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, locale: Locale) -> None:
        self.locale = locale
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
        return [e for e in self.entities.values() if e.role in {"captain", "engineer"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.locale)
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


def _r_trapped_creature(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["imprisoned"] < THRESHOLD:
        return []
    sig = ("fear", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.memes["fear"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__fear__"]


def _r_argument_to_distance(world: World) -> list[str]:
    a = world.get("hero")
    b = world.get("friend")
    if a.memes["argument"] < THRESHOLD or b.memes["argument"] < THRESHOLD:
        return []
    sig = ("distance", a.id, b.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.meters["distance"] += 1
    b.meters["distance"] += 1
    return ["__distance__"]


CAUSAL_RULES = [
    Rule(name="trapped_creature", tag="emotional", apply=_r_trapped_creature),
    Rule(name="argument_to_distance", tag="social", apply=_r_argument_to_distance),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


LOCALES = {
    "moon_base": Locale(
        id="moon_base",
        place="the silver moon base",
        vehicle="their little rover",
        sky="a black sky full of stars",
        mission="mapping the tunnels under the moon base",
        affords={"bubble_field", "jammed_door"},
        tags={"moon", "space"},
    ),
    "ring_station": Locale(
        id="ring_station",
        place="the bright ring station",
        vehicle="their shuttle pod",
        sky="the blue curve of a giant planet outside the glass",
        mission="checking the humming halls of ring station",
        affords={"bubble_field", "crate_latch", "jammed_door"},
        tags={"station", "space"},
    ),
    "asteroid_cave": Locale(
        id="asteroid_cave",
        place="the crystal asteroid cave",
        vehicle="their tiny scout ship",
        sky="sparkling dust drifting past the cave mouth",
        mission="following a beacon through an asteroid cave",
        affords={"crate_latch", "jammed_door"},
        tags={"asteroid", "space"},
    ),
}

PRISONS = {
    "bubble_field": Prison(
        id="bubble_field",
        label="bubble field",
        phrase="a round bubble field",
        lock_type="field",
        opener="hush key",
        fear_reason="the station's safety net had mistaken the little visitor for loose cargo",
        allowed_locales={"moon_base", "ring_station"},
        tags={"bubble", "safety_system"},
    ),
    "crate_latch": Prison(
        id="crate_latch",
        label="cargo crate",
        phrase="a clear cargo crate with a red latch",
        lock_type="latch",
        opener="star wrench",
        fear_reason="an automatic loader had scooped the tiny creature up with the supply boxes",
        allowed_locales={"ring_station", "asteroid_cave"},
        tags={"crate", "cargo"},
    ),
    "jammed_door": Prison(
        id="jammed_door",
        label="maintenance room",
        phrase="a tiny maintenance room with a stuck sliding door",
        lock_type="door",
        opener="magnet patch",
        fear_reason="the old door had slid shut during a power wobble and would not open again",
        allowed_locales={"moon_base", "ring_station", "asteroid_cave"},
        tags={"door", "maintenance"},
    ),
}

TOOLS = {
    "hush_key": Tool(
        id="hush_key",
        label="hush key",
        phrase="the hush key",
        works_on={"field"},
        method="held the hush key to the glowing seam until the bubble field sighed and melted away",
        fail="pressed the hush key against the wrong kind of lock, and nothing changed",
        tags={"key", "tool"},
    ),
    "star_wrench": Tool(
        id="star_wrench",
        label="star wrench",
        phrase="the star wrench",
        works_on={"latch"},
        method="turned the red latch with the star wrench until the crate clicked open",
        fail="twisted the star wrench at a seal with no bolt to turn, and the prison stayed shut",
        tags={"wrench", "tool"},
    ),
    "magnet_patch": Tool(
        id="magnet_patch",
        label="magnet patch",
        phrase="the magnet patch",
        works_on={"door"},
        method="slapped the magnet patch on the crooked rail and pulled until the stuck door slid free",
        fail="stuck the magnet patch to a surface that had no rail to guide, and the prison stayed shut",
        tags={"magnet", "tool"},
    ),
    "sole_badge": Tool(
        id="sole_badge",
        label="sole captain badge",
        phrase="the sole captain badge",
        works_on=set(),
        method="",
        fail="waved the sole captain badge in front of the lock, but a badge is not a tool for opening that prison",
        tags={"badge"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nova", "Aya", "Pia", "Rin", "Zuri"]
BOY_NAMES = ["Jax", "Milo", "Oren", "Kai", "Nico", "Tao", "Rex", "Ivo"]
TRAITS = ["brave", "careful", "curious", "kind", "quick-thinking", "steady"]


def prison_fits_locale(locale_id: str, prison_id: str) -> bool:
    return prison_id in LOCALES[locale_id].affords and locale_id in PRISONS[prison_id].allowed_locales


def tool_works(tool_id: str, prison_id: str) -> bool:
    return PRISONS[prison_id].lock_type in TOOLS[tool_id].works_on


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for locale_id in LOCALES:
        for prison_id in PRISONS:
            if not prison_fits_locale(locale_id, prison_id):
                continue
            for tool_id in TOOLS:
                if tool_works(tool_id, prison_id):
                    combos.append((locale_id, prison_id, tool_id))
    return combos


@dataclass
class StoryParams:
    locale: str
    prison: str
    tool: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    hero_trait: str
    friend_trait: str
    apology_first: bool = True
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, friend: Entity, parent: Entity) -> None:
    locale = world.locale
    world.say(
        f"{hero.id} and {friend.id} were junior space explorers on {locale.place}. "
        f"They rode in {locale.vehicle} under {locale.sky}, busy with {locale.mission}."
    )
    world.say(
        f"{hero.id} wore the sole captain badge that day, and {friend.id} carried the tool pouch. "
        f"Both wanted to lead, which made their adventure feel a little prickly from the start."
    )
    world.facts["parent_word"] = parent.label_word


def begin_argument(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["argument"] += 1
    friend.memes["argument"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I am the captain today," {hero.id} said. "{friend.id}, just follow my map."'
    )
    world.say(
        f'{friend.id} folded {friend.pronoun("possessive")} arms. '
        f'"Your map missed the last turn. Maybe you should listen to my scanner for once."'
    )


def hear_cry(world: World, creature: Entity, prison: Prison) -> None:
    creature.meters["imprisoned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before either child could answer, a tiny peeping sound echoed through the hall. "
        f"Behind a stack of glowing pipes sat {prison.phrase}, and inside it fluttered {creature.label}."
    )
    world.say(
        f"It was clear the lock did not mean to imprison anyone forever. {prison.fear_reason}."
    )


def inspect_prison(world: World, hero: Entity, friend: Entity, prison: Prison, tool: Tool) -> None:
    creature = world.get("creature")
    world.say(
        f"{creature.label.capitalize()} tapped the barrier with its bright nose and looked terribly small. "
        f"{friend.id} knelt beside it while {hero.id} studied the lock."
    )
    world.say(
        f'"We have to solve this," {hero.id} whispered. '
        f'"{tool.phrase.capitalize()} should open a {prison.label} like this."'
    )


def quarrel_blocks_solution(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["stuck"] += 1
    friend.memes["stuck"] += 1
    world.say(
        f"But their argument was still sitting between them like a box in the middle of the floor. "
        f"{hero.id} reached first, {friend.id} reached second, and they bumped shoulders instead of helping."
    )


def reconcile(world: World, hero: Entity, friend: Entity, apology_first: bool) -> None:
    if apology_first:
        first, second = hero, friend
    else:
        first, second = friend, hero
    first.memes["sorry"] += 1
    second.memes["forgive"] += 1
    hero.memes["argument"] = 0.0
    friend.memes["argument"] = 0.0
    hero.meters["distance"] = 0.0
    friend.meters["distance"] = 0.0
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'"Wait," {first.id} said. "I was pulling too hard to be the boss. I am sorry."'
    )
    world.say(
        f'{second.id} took a slow breath and nodded. '
        f'"I am sorry too. Let us do this together."'
    )
    world.say(
        f"That small moment of reconciliation changed the room. The children stepped close again, "
        f"one holding the light steady while the other reached for the tool."
    )


def solve_success(world: World, hero: Entity, friend: Entity, prison: Prison, tool: Tool) -> None:
    creature = world.get("creature")
    helper = hero if hero.memes["trust"] >= friend.memes["trust"] else friend
    other = friend if helper is hero else hero
    creature.meters["imprisoned"] = 0.0
    creature.memes["fear"] = 0.0
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    creature.memes["relief"] += 1
    world.say(
        f"{helper.id} used {tool.phrase} while {other.id} steadied the panel and counted softly. "
        f"Together they {tool.method}."
    )
    world.say(
        f"{creature.label.capitalize()} zipped out, circled their helmets in a shining loop, and chirped a happy song."
    )


def solve_fail(world: World, hero: Entity, friend: Entity, tool: Tool) -> None:
    creature = world.get("creature")
    creature.memes["fear"] += 1
    hero.memes["sad"] += 1
    friend.memes["sad"] += 1
    world.say(
        f"They tried anyway, but they {tool.fail}. The tiny alien shrank back, and both children knew guessing had not helped."
    )
    world.say(
        f"So they sent a careful call to station control and stayed beside {creature.label}, promising not to leave it alone."
    )


def kind_ending(world: World, hero: Entity, friend: Entity, creature: Entity, parent: Entity) -> None:
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"Instead of darting away, {creature.label} landed on the rail between them and touched both gloves with its little paws."
    )
    world.say(
        f'{parent.label_word.capitalize()} arrived on the radio a moment later and said, '
        f'"That was brave work. The best captains know when to share the map."'
    )
    world.say(
        f"{hero.id} laughed, {friend.id} laughed too, and the rest of the mission felt bigger and brighter because neither one wanted to be the sole hero anymore."
    )


def gentle_wait_ending(world: World, hero: Entity, friend: Entity, parent: Entity) -> None:
    world.say(
        f'{parent.label_word.capitalize()} answered their call at once and told them to keep the frightened creature company until help arrived.'
    )
    world.say(
        f"So {hero.id} and {friend.id} sat side by side at last, speaking softly through the barrier until the alien stopped trembling."
    )
    world.say(
        f"Even before the grown-ups came, the children had learned something important: a problem is easier to solve when nobody is trying to be the sole hero."
    )


def tell(
    locale: Locale,
    prison: Prison,
    tool: Tool,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    friend_name: str = "Milo",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    hero_trait: str = "brave",
    friend_trait: str = "careful",
    apology_first: bool = True,
) -> World:
    world = World(locale)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="captain", traits=[hero_trait]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="engineer", traits=[friend_trait]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    creature = world.add(Entity(id="creature", kind="character", type="alien", label="the starling sprite", role="creature"))
    world.facts["display_names"] = {"hero": hero_name, "friend": friend_name}

    introduce(world, hero, friend, parent)
    begin_argument(world, hero, friend)

    world.para()
    hear_cry(world, creature, prison)
    inspect_prison(world, hero, friend, prison, tool)
    quarrel_blocks_solution(world, hero, friend)

    world.para()
    reconcile(world, hero, friend, apology_first=apology_first)

    success = tool_works(tool.id, prison.id)
    if success:
        solve_success(world, hero, friend, prison, tool)
        world.para()
        kind_ending(world, hero, friend, creature, parent)
        outcome = "freed"
    else:
        solve_fail(world, hero, friend, tool)
        world.para()
        gentle_wait_ending(world, hero, friend, parent)
        outcome = "waiting"

    world.facts.update(
        locale=locale,
        prison=prison,
        tool=tool,
        hero=hero,
        friend=friend,
        parent=parent,
        creature=creature,
        reconciled=hero.memes["trust"] >= THRESHOLD and friend.memes["trust"] >= THRESHOLD,
        outcome=outcome,
        success=success,
    )
    return world


def display_name(ent: Entity) -> str:
    names = ent.attrs.get("display_name")
    if names:
        return str(names)
    return ent.label or ent.id


def hero_name(world: World) -> str:
    return world.facts.get("display_names", {}).get("hero", world.get("hero").label)


def friend_name(world: World) -> str:
    return world.facts.get("display_names", {}).get("friend", world.get("friend").label)


KNOWLEDGE = {
    "space": [
        (
            "What is a space station?",
            "A space station is a place built in space where people can live and work for a while. It has rooms, tools, and safety systems, just like a tiny town floating above a planet.",
        )
    ],
    "moon": [
        (
            "Why do astronauts use rovers on the moon?",
            "Rovers help astronauts and explorers travel over the moon's dusty ground. They can carry tools and help people move farther than they could on foot.",
        )
    ],
    "bubble": [
        (
            "What is a force field or bubble field in a pretend space story?",
            "In a pretend space story, a bubble field is an invisible wall made by a machine. It can hold something safely in one place without using chains or bars.",
        )
    ],
    "crate": [
        (
            "What is a cargo crate?",
            "A cargo crate is a strong box used to carry supplies from one place to another. On a station or ship, it helps keep tools and food from floating away.",
        )
    ],
    "door": [
        (
            "Why can a sliding door get stuck?",
            "A sliding door can get stuck if its rail is bent, dusty, or out of line. Then it needs the right tool or a careful repair to move smoothly again.",
        )
    ],
    "tool": [
        (
            "Why is the right tool important?",
            "The right tool fits the job you are doing. When you use the wrong tool, the problem usually stays the same or gets harder to fix.",
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people stop fighting and come back together after hurt feelings. They listen, say sorry, and choose peace again.",
        )
    ],
    "alien": [
        (
            "Why should you be gentle with a scared creature?",
            "A scared creature does not know yet if it is safe. Gentle voices and calm actions help it feel protected instead of more frightened.",
        )
    ],
}

KNOWLEDGE_ORDER = ["space", "moon", "bubble", "crate", "door", "tool", "reconciliation", "alien"]


def generation_prompts(world: World) -> list[str]:
    locale = world.facts["locale"]
    prison = world.facts["prison"]
    tool = world.facts["tool"]
    hname = hero_name(world)
    fname = friend_name(world)
    return [
        'Write a short space adventure for a 3-to-5-year-old that includes the words "solve", "sole", and "imprison".',
        f"Tell a gentle story where {hname} and {fname} are arguing on {locale.place} when they find a tiny alien trapped in {prison.phrase}, and they must reconcile to solve the problem together.",
        f"Write a child-friendly rescue tale about two young explorers who stop trying to be the sole hero, use {tool.phrase}, and free a frightened creature without any villain at all.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    parent = world.facts["parent"]
    creature = world.facts["creature"]
    prison = world.facts["prison"]
    tool = world.facts["tool"]
    locale = world.facts["locale"]
    hname = hero_name(world)
    fname = friend_name(world)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young space explorers, {hname} and {fname}, and a tiny alien called {creature.label}. They meet while exploring {locale.place}.",
        ),
        (
            "What problem did the children find?",
            f"They found {creature.label} trapped inside {prison.phrase}. The lock did not mean to be cruel; it had made a scared mistake and ended up trying to imprison the little visitor.",
        ),
        (
            f"Why could the children not solve the problem right away?",
            f"They were still in the middle of an argument about who should lead. Because they were pulling apart instead of working together, they kept bumping and getting in each other's way.",
        ),
        (
            "What changed when they reconciled?",
            f"They said sorry and stepped close again instead of fighting over the job. That reconciliation let one child hold things steady while the other used the tool properly.",
        ),
    ]
    if world.facts["success"]:
        qa.append(
            (
                f"How did {hname} and {fname} free the trapped creature?",
                f"They worked together with {tool.phrase} and opened the {prison.label}. The rescue worked because the tool matched the lock and the children had stopped arguing long enough to use it carefully.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with relief and friendship. {creature.label.capitalize()} came out safely, and the children learned they did not need to be the sole hero to be brave.",
            )
        )
    else:
        qa.append(
            (
                "Did the first try work?",
                f"No. Their first try did not work because the tool was wrong for that kind of lock. After that, they stayed calm, called for help, and kept the creature company instead of making the problem worse.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended gently, with the children waiting together for help. Even before the prison opened, they had already changed by stopping their fight and acting kindly side by side.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"space", "reconciliation", "alien", "tool"}
    locale = world.facts["locale"]
    prison = world.facts["prison"]
    if "moon" in locale.tags:
        tags.add("moon")
    if "bubble" in prison.tags:
        tags.add("bubble")
    if "crate" in prison.tags:
        tags.add("crate")
    if "door" in prison.tags:
        tags.add("door")
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
    shown_names = world.facts.get("display_names", {})
    lines = ["--- world model state ---"]
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if eid in shown_names:
            bits.append(f"name={shown_names[eid]}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {eid:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        locale="moon_base",
        prison="bubble_field",
        tool="hush_key",
        hero_name="Nova",
        hero_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        parent="mother",
        hero_trait="brave",
        friend_trait="careful",
        apology_first=True,
    ),
    StoryParams(
        locale="ring_station",
        prison="crate_latch",
        tool="star_wrench",
        hero_name="Jax",
        hero_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        parent="father",
        hero_trait="quick-thinking",
        friend_trait="kind",
        apology_first=False,
    ),
    StoryParams(
        locale="asteroid_cave",
        prison="jammed_door",
        tool="magnet_patch",
        hero_name="Tessa",
        hero_gender="girl",
        friend_name="Kai",
        friend_gender="boy",
        parent="mother",
        hero_trait="curious",
        friend_trait="steady",
        apology_first=True,
    ),
]


def explain_rejection(locale_id: str, prison_id: str, tool_id: str) -> str:
    if not prison_fits_locale(locale_id, prison_id):
        return (
            f"(No story: {PRISONS[prison_id].label} does not belong in {LOCALES[locale_id].place}. "
            f"Pick a prison type that fits that location.)"
        )
    if not tool_works(tool_id, prison_id):
        return (
            f"(No story: {TOOLS[tool_id].label} cannot open {PRISONS[prison_id].label}. "
            f"The fix must genuinely match the lock.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
valid(Locale, Prison, Tool) :-
    locale(Locale), prison(Prison), tool(Tool),
    affords(Locale, Prison), allowed(Prison, Locale),
    lock_type(Prison, Lock), works_on(Tool, Lock).

success :- chosen_prison(P), chosen_tool(T),
           lock_type(P, L), works_on(T, L).

outcome(freed)   :- success.
outcome(waiting) :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for locale_id, locale in LOCALES.items():
        lines.append(asp.fact("locale", locale_id))
        for prison_id in sorted(locale.affords):
            lines.append(asp.fact("affords", locale_id, prison_id))
    for prison_id, prison in PRISONS.items():
        lines.append(asp.fact("prison", prison_id))
        lines.append(asp.fact("lock_type", prison_id, prison.lock_type))
        for locale_id in sorted(prison.allowed_locales):
            lines.append(asp.fact("allowed", prison_id, locale_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for lock in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tool_id, lock))
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
            asp.fact("chosen_prison", params.prison),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "freed" if tool_works(params.tool, params.prison) else "waiting"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small space adventure about freeing a trapped creature through reconciliation."
    )
    ap.add_argument("--locale", choices=LOCALES)
    ap.add_argument("--prison", choices=PRISONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--no-apology-first", action="store_true", help="have the friend apologize first")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.locale and args.prison and args.tool:
        if not (prison_fits_locale(args.locale, args.prison) and tool_works(args.tool, args.prison)):
            raise StoryError(explain_rejection(args.locale, args.prison, args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.locale is None or combo[0] == args.locale)
        and (args.prison is None or combo[1] == args.prison)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        if args.locale and args.prison and args.tool:
            raise StoryError(explain_rejection(args.locale, args.prison, args.tool))
        raise StoryError("(No valid combination matches the given options.)")

    locale_id, prison_id, tool_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name_value = args.hero_name or pick_name(rng, hero_gender)
    friend_name_value = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name_value)
    parent_type = args.parent or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice([t for t in TRAITS if t != hero_trait] or TRAITS)
    return StoryParams(
        locale=locale_id,
        prison=prison_id,
        tool=tool_id,
        hero_name=hero_name_value,
        hero_gender=hero_gender,
        friend_name=friend_name_value,
        friend_gender=friend_gender,
        parent=parent_type,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
        apology_first=not args.no_apology_first,
    )


def generate(params: StoryParams) -> StorySample:
    if params.locale not in LOCALES:
        raise StoryError(f"(Invalid locale: {params.locale})")
    if params.prison not in PRISONS:
        raise StoryError(f"(Invalid prison: {params.prison})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if not prison_fits_locale(params.locale, params.prison):
        raise StoryError(explain_rejection(params.locale, params.prison, params.tool))
    if not tool_works(params.tool, params.prison):
        raise StoryError(explain_rejection(params.locale, params.prison, params.tool))

    world = tell(
        locale=LOCALES[params.locale],
        prison=PRISONS[params.prison],
        tool=TOOLS[params.tool],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
        apology_first=params.apology_first,
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

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive for batch verification
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
        print(f"{len(combos)} compatible (locale, prison, tool) combos:\n")
        for locale_id, prison_id, tool_id in combos:
            print(f"  {locale_id:13} {prison_id:12} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.prison} on {p.locale} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
