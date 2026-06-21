#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/beer_similar_quest_flashback_tall_tale.py
====================================================================

A standalone story world for a child-sized tall tale about a fizzy **root beer**
delivery quest. The hero must carry a grand, foamy treat across one outsized
obstacle. An elder remembers a **similar** trouble from long ago, tells a brief
flashback, and that remembered method becomes the turn that saves the day.

The domain is intentionally small and constraint-checked:

    obstacle + wrong tool -> rejected as unreasonable
    obstacle + matching tool -> a plausible quest story

This world keeps the prose child-facing by making the drink explicitly root beer,
a sweet fizzy drink, not alcohol.

Run it
------
    python storyworlds/worlds/gpt-5.4/beer_similar_quest_flashback_tall_tale.py
    python storyworlds/worlds/gpt-5.4/beer_similar_quest_flashback_tall_tale.py --obstacle wind --tool lid
    python storyworlds/worlds/gpt-5.4/beer_similar_quest_flashback_tall_tale.py --obstacle bridge --tool wagon
    python storyworlds/worlds/gpt-5.4/beer_similar_quest_flashback_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/beer_similar_quest_flashback_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/beer_similar_quest_flashback_tall_tale.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "aunt", "mother"}
        male = {"boy", "man", "grandfather", "uncle", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "grandfather": "grandpa",
            "grandmother": "grandma",
            "mother": "mom",
            "father": "dad",
        }
        return mapping.get(self.type, self.type)


@dataclass
class ContainerCfg:
    id: str
    label: str
    phrase: str
    grand_phrase: str
    carry_verb: str
    foam_line: str
    size: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ObstacleCfg:
    id: str
    label: str
    phrase: str
    threat: str
    required_tool: str
    memory_line: str
    pass_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolCfg:
    id: str
    label: str
    phrase: str
    action_line: str
    method_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DestinationCfg:
    id: str
    label: str
    phrase: str
    need_line: str
    cheer_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    container: str
    obstacle: str
    tool: str
    destination: str
    hero_name: str
    hero_gender: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None


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


def _r_risk(world: World) -> list[str]:
    cargo = world.get("cargo")
    obstacle = world.get("obstacle")
    tool = world.get("tool")
    if cargo.meters["journey"] < THRESHOLD:
        return []
    if tool.attrs.get("matches") == obstacle.id:
        return []
    sig = ("risk", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["spill_risk"] += 1
    cargo.meters["slosh"] += 1
    hero = world.get("hero")
    hero.memes["worry"] += 1
    return [f"The {cargo.label} gave a nervous slosh as the {obstacle.label} loomed ahead."]


def _r_secure(world: World) -> list[str]:
    cargo = world.get("cargo")
    obstacle = world.get("obstacle")
    tool = world.get("tool")
    if cargo.meters["journey"] < THRESHOLD:
        return []
    if tool.attrs.get("matches") != obstacle.id:
        return []
    sig = ("secure", obstacle.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["steady"] += 1
    hero = world.get("hero")
    hero.memes["courage"] += 1
    hero.memes["trust"] += 1
    return [f"With the {tool.label} in place, the root beer settled down as if it had remembered its manners."]


def _r_deliver(world: World) -> list[str]:
    cargo = world.get("cargo")
    if cargo.meters["steady"] < THRESHOLD or cargo.meters["crossed"] < THRESHOLD:
        return []
    sig = ("deliver",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["delivered"] += 1
    hero = world.get("hero")
    helper = world.get("elder")
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="secure", tag="physical", apply=_r_secure),
    Rule(name="deliver", tag="social", apply=_r_deliver),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


CONTAINERS = {
    "mug": ContainerCfg(
        id="mug",
        label="mug",
        phrase="a frosty mug of root beer",
        grand_phrase="a frosty mug of root beer with foam stacked as high as a squirrel's dream",
        carry_verb="held with both hands",
        foam_line="Foam peeked over the rim like a little white cloud.",
        size=1,
        tags={"root_beer"},
    ),
    "jug": ContainerCfg(
        id="jug",
        label="jug",
        phrase="a glass jug of root beer",
        grand_phrase="a glass jug of root beer so fizzy it looked ready to sing",
        carry_verb="hugged against a chest",
        foam_line="Bubbles climbed the glass in silver strings.",
        size=2,
        tags={"root_beer", "fizz"},
    ),
    "barrel": ContainerCfg(
        id="barrel",
        label="barrel",
        phrase="a small barrel of root beer",
        grand_phrase="a small barrel of root beer, though anyone listening would swear it was the size of a moon",
        carry_verb="rolled and guided",
        foam_line="A cool ring of foam trembled at the bung.",
        size=3,
        tags={"root_beer", "fizz"},
    ),
}

OBSTACLES = {
    "wind": ObstacleCfg(
        id="wind",
        label="windy hill",
        phrase="the windy hill",
        threat="One wild puff could slap the foam right out of the top.",
        required_tool="lid",
        memory_line="once crossed a similar windy hill with a pie that tried to fly clear to the county line",
        pass_line="The wind huffed and puffed, but it could not steal a single fizz.",
        ending_image="The root beer arrived with its foamy crown still standing straight.",
        tags={"wind", "weather"},
    ),
    "bridge": ObstacleCfg(
        id="bridge",
        label="wobble bridge",
        phrase="the wobble bridge",
        threat="Every plank bounced like a jumping bean, ready to jiggle the drink loose.",
        required_tool="rope",
        memory_line="once crossed a similar wobble bridge with a basket of peaches that wanted to hop into the creek",
        pass_line="The bridge boinged and bounced, but the cargo kept step and never tipped.",
        ending_image="The root beer reached the far side as neat as if it had ridden on rails.",
        tags={"bridge", "balance"},
    ),
    "ruts": ObstacleCfg(
        id="ruts",
        label="rutted lane",
        phrase="the rutted lane",
        threat="Those wagon-deep holes could jolt the root beer into a foamy tantrum.",
        required_tool="wagon",
        memory_line="once followed a similar rutted lane with a basket of eggs and not one of them cracked",
        pass_line="The wheels bumped and hummed, but the root beer rode smooth and proud.",
        ending_image="The root beer rolled in without so much as a wasted bubble.",
        tags={"road", "wagon"},
    ),
}

TOOLS = {
    "lid": ToolCfg(
        id="lid",
        label="tin lid",
        phrase="a bright tin lid",
        action_line="snapped the bright tin lid snug over the top",
        method_line="A good lid keeps the foam home when the sky starts showing off.",
        tags={"lid", "fizz"},
    ),
    "rope": ToolCfg(
        id="rope",
        label="looped rope",
        phrase="a looped rope handle",
        action_line="tied on a looped rope handle so the load could sway without slipping",
        method_line="When a bridge dances, you let your hands dance with it.",
        tags={"rope", "balance"},
    ),
    "wagon": ToolCfg(
        id="wagon",
        label="red wagon",
        phrase="a red wagon with stout wheels",
        action_line="set the load in a red wagon with stout wheels",
        method_line="Let wheels talk to ruts, and the arms can save their strength.",
        tags={"wagon", "road"},
    ),
}

DESTINATIONS = {
    "picnic": DestinationCfg(
        id="picnic",
        label="orchard picnic",
        phrase="the orchard picnic",
        need_line="The town band had finished marching, and everyone was hot and thirsty.",
        cheer_line="Paper cups popped up like flowers, and the first sip made the whole orchard grin.",
        tags={"picnic"},
    ),
    "bandstand": DestinationCfg(
        id="bandstand",
        label="bandstand",
        phrase="the bandstand supper",
        need_line="The fiddlers were tuning up, and supper would not feel complete without something cold and sweet.",
        cheer_line="The fiddlers laughed, the cups clinked, and the tune after supper sounded twice as lively.",
        tags={"music"},
    ),
    "hayfield": DestinationCfg(
        id="hayfield",
        label="hayfield lunch",
        phrase="the hayfield lunch",
        need_line="The hay crew had stacked hay till their hats looked tired.",
        cheer_line="The workers tipped back their cups, and even the scarecrow seemed to stand a little straighter.",
        tags={"field"},
    ),
}

GIRL_NAMES = ["Molly", "Nell", "Pearl", "Daisy", "June", "Cora"]
BOY_NAMES = ["Jed", "Eli", "Toby", "Cal", "Finn", "Wade"]
ELDERS = [
    {"name": "Grandpa Gus", "type": "grandfather"},
    {"name": "Grandma May", "type": "grandmother"},
    {"name": "Uncle Roy", "type": "uncle"},
    {"name": "Aunt Bea", "type": "aunt"},
]


def valid_combo(container_id: str, obstacle_id: str, tool_id: str, destination_id: str) -> bool:
    if container_id not in CONTAINERS or obstacle_id not in OBSTACLES or tool_id not in TOOLS or destination_id not in DESTINATIONS:
        return False
    return OBSTACLES[obstacle_id].required_tool == tool_id


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for container_id in sorted(CONTAINERS):
        for obstacle_id, obstacle in OBSTACLES.items():
            for destination_id in sorted(DESTINATIONS):
                combos.append((container_id, obstacle_id, obstacle.required_tool, destination_id))
    return sorted(combos)


def explain_rejection(obstacle_id: str, tool_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    needed = TOOLS[obstacle.required_tool].label
    got = TOOLS[tool_id].label
    return (
        f"(No story: the {obstacle.label} needs the {needed}, not the {got}. "
        f"The quest only works when the chosen tool truly solves the obstacle.)"
    )


def introduce(world: World, hero: Entity, elder: Entity, cargo: Entity, destination: DestinationCfg) -> None:
    world.say(
        f"In a town where stories grew taller than the church steeple, {hero.id} was sent on a quest. "
        f"{destination.need_line}"
    )
    world.say(
        f"So {elder.id} pointed to {cargo.phrase} and said it must be carried to {destination.phrase} before the ice melted and the fizz lost heart."
    )
    world.say(cargo.attrs["foam_line"])


def vow(world: World, hero: Entity, cargo: Entity) -> None:
    hero.memes["duty"] += 1
    world.say(
        f'{hero.id} {cargo.attrs["carry_verb"]} and made a vow brave enough to tickle the clouds. '
        f'"I will get this root beer there if I have to outwalk the wind, outbounce the bridge, or outstare the road itself!"'
    )


def meet_obstacle(world: World, hero: Entity, obstacle: Entity) -> None:
    cargo = world.get("cargo")
    cargo.meters["journey"] += 1
    world.say(
        f"But before long the path pinched itself into {obstacle.attrs["phrase"]}. {obstacle.attrs["threat"]}"
    )
    propagate(world, narrate=True)
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id} slowed to a careful stop. Even in a tall tale, a spill is a spill."
        )


def flashback(world: World, elder: Entity, obstacle_cfg: ObstacleCfg, tool_cfg: ToolCfg) -> None:
    elder.memes["memory"] += 1
    hero = world.get("hero")
    hero.memes["hope"] += 1
    world.say(
        f"That sight pulled a flashback out of {elder.id} as quick as pulling a rabbit from a hat. "
        f"{elder.pronoun().capitalize()} said {elder.pronoun()} {obstacle_cfg.memory_line}."
    )
    world.say(
        f'"It was a similar scrape," {elder.pronoun()} said, tapping {tool_cfg.phrase}. '
        f'"{tool_cfg.method_line}"'
    )


def equip_tool(world: World, tool_cfg: ToolCfg) -> None:
    tool = world.get("tool")
    tool.meters["ready"] += 1
    world.say(
        f"So they {tool_cfg.action_line}."
    )
    propagate(world, narrate=True)


def cross(world: World, hero: Entity, obstacle_cfg: ObstacleCfg) -> None:
    cargo = world.get("cargo")
    cargo.meters["crossed"] += 1
    propagate(world, narrate=False)
    if cargo.meters["steady"] >= THRESHOLD:
        hero.memes["relief"] += 1
        world.say(obstacle_cfg.pass_line)
    else:
        raise StoryError("The cargo was not secured before the crossing.")


def arrive(world: World, hero: Entity, elder: Entity, destination_cfg: DestinationCfg, obstacle_cfg: ObstacleCfg) -> None:
    cargo = world.get("cargo")
    propagate(world, narrate=False)
    if cargo.meters["delivered"] < THRESHOLD:
        raise StoryError("The quest did not finish in delivery.")
    world.say(
        f"At last they marched into {destination_cfg.phrase} with the root beer still cool and lively. {destination_cfg.cheer_line}"
    )
    world.say(
        f"{elder.id} winked at {hero.id}, and {hero.id} stood a little taller than before. {obstacle_cfg.ending_image}"
    )


def tell(container_cfg: ContainerCfg, obstacle_cfg: ObstacleCfg, tool_cfg: ToolCfg,
         destination_cfg: DestinationCfg, hero_name: str, hero_gender: str,
         elder_name: str, elder_type: str) -> World:
    if obstacle_cfg.required_tool != tool_cfg.id:
        raise StoryError(explain_rejection(obstacle_cfg.id, tool_cfg.id))

    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name, phrase=elder_name, role="elder"))
    cargo = world.add(Entity(
        id="cargo",
        kind="thing",
        type="drink",
        label=container_cfg.label,
        phrase=container_cfg.grand_phrase,
        role="cargo",
        attrs={"foam_line": container_cfg.foam_line, "carry_verb": container_cfg.carry_verb},
        tags=set(container_cfg.tags),
    ))
    obstacle = world.add(Entity(
        id=obstacle_cfg.id,
        kind="thing",
        type="obstacle",
        label=obstacle_cfg.label,
        phrase=obstacle_cfg.phrase,
        role="obstacle",
        attrs={"phrase": obstacle_cfg.phrase, "threat": obstacle_cfg.threat},
        tags=set(obstacle_cfg.tags),
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        role="tool",
        attrs={"matches": tool_cfg.id},
        tags=set(tool_cfg.tags),
    ))

    world.para()
    introduce(world, hero, elder, cargo, destination_cfg)
    vow(world, hero, cargo)

    world.para()
    meet_obstacle(world, hero, obstacle)
    flashback(world, elder, obstacle_cfg, tool_cfg)

    world.para()
    equip_tool(world, tool_cfg)
    cross(world, hero, obstacle_cfg)

    world.para()
    arrive(world, hero, elder, destination_cfg, obstacle_cfg)

    world.facts.update(
        hero=hero,
        elder=elder,
        cargo=cargo,
        obstacle_cfg=obstacle_cfg,
        tool_cfg=tool_cfg,
        destination_cfg=destination_cfg,
        delivered=cargo.meters["delivered"] >= THRESHOLD,
        worried=hero.memes["worry"] >= THRESHOLD,
        flashback=elder.memes["memory"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "root_beer": [(
        "What is root beer?",
        "Root beer is a sweet fizzy drink. In stories like this one, it is a treat for families and children, not an alcoholic drink."
    )],
    "fizz": [(
        "Why does a fizzy drink need to be carried carefully?",
        "A fizzy drink has bubbles in it, so shaking it too much can make the foam rise and spill. Carrying it gently keeps more of the drink inside."
    )],
    "wind": [(
        "Why can wind make carrying a drink hard?",
        "Wind can push your hands and the cup or jug you are carrying. That sudden push can slosh the drink over the top."
    )],
    "bridge": [(
        "Why is a wobbly bridge tricky?",
        "A wobbly bridge moves under your feet, so you have to balance carefully. If what you carry sways too much, it can tip."
    )],
    "road": [(
        "What are ruts in a road?",
        "Ruts are long dents or grooves in the ground made by wheels. They can make a ride bumpy."
    )],
    "lid": [(
        "What does a lid do?",
        "A lid covers the top of a cup, mug, or jug. It helps keep splashes and foam from spilling out."
    )],
    "rope": [(
        "Why can a rope handle help carry something?",
        "A rope handle gives your hands a steady way to hold and guide a load. It can help you balance when the path moves under you."
    )],
    "wagon": [(
        "What is a wagon for?",
        "A wagon helps carry heavy things on wheels. Its wheels can do the rolling work so your arms do not have to."
    )],
    "flashback": [(
        "What is a flashback in a story?",
        "A flashback is a short memory scene from an earlier time. It shows something from the past that helps explain the present."
    )],
    "quest": [(
        "What is a quest?",
        "A quest is a journey with a clear job or goal. Someone sets out, faces trouble, and keeps going until the task is done."
    )],
}
KNOWLEDGE_ORDER = ["quest", "flashback", "root_beer", "fizz", "wind", "bridge", "road", "lid", "rope", "wagon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    obstacle_cfg = f["obstacle_cfg"]
    destination_cfg = f["destination_cfg"]
    tool_cfg = f["tool_cfg"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old about a quest to deliver root beer, and include the word "similar".',
        f"Tell a child-friendly tall tale where {hero.label} must carry root beer to {destination_cfg.phrase}, faces {obstacle_cfg.phrase}, and is helped by a flashback from {elder.label}.",
        f"Write a story with a quest, a flashback, and a clever tool: the obstacle is {obstacle_cfg.label}, the helper uses {tool_cfg.label}, and the ending proves the root beer arrived safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    obstacle_cfg = f["obstacle_cfg"]
    tool_cfg = f["tool_cfg"]
    destination_cfg = f["destination_cfg"]
    cargo = f["cargo"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who goes on a quest to carry root beer, and {elder.label}, who helps with wise advice from the past."
        ),
        (
            "What was the quest?",
            f"The quest was to bring {cargo.phrase} to {destination_cfg.phrase}. The trip mattered because people there were waiting for something cold and sweet."
        ),
        (
            f"What trouble stood in {hero.label}'s way?",
            f"The trouble was {obstacle_cfg.phrase}. It was dangerous because {obstacle_cfg.threat.lower()}"
        ),
        (
            f"What happened in the flashback?",
            f"{elder.label} remembered {elder.pronoun()} {obstacle_cfg.memory_line}. That memory mattered because it showed a similar problem and pointed to the right tool."
        ),
        (
            f"How did {hero.label} solve the problem?",
            f"They used {tool_cfg.phrase}. {tool_cfg.method_line} That helped the root beer stay steady while they crossed the obstacle."
        ),
        (
            "How did the story end?",
            f"The quest ended happily at {destination_cfg.phrase}, where the root beer arrived safely. The final image proves what changed: {obstacle_cfg.ending_image.lower()}"
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"quest", "flashback"}
    tags |= set(world.facts["cargo"].tags)
    tags |= set(world.facts["obstacle_cfg"].tags)
    tags |= set(world.facts["tool_cfg"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        container="mug",
        obstacle="wind",
        tool="lid",
        destination="picnic",
        hero_name="Molly",
        hero_gender="girl",
        elder_name="Grandpa Gus",
        elder_type="grandfather",
    ),
    StoryParams(
        container="jug",
        obstacle="bridge",
        tool="rope",
        destination="bandstand",
        hero_name="Eli",
        hero_gender="boy",
        elder_name="Grandma May",
        elder_type="grandmother",
    ),
    StoryParams(
        container="barrel",
        obstacle="ruts",
        tool="wagon",
        destination="hayfield",
        hero_name="Pearl",
        hero_gender="girl",
        elder_name="Uncle Roy",
        elder_type="uncle",
    ),
]


ASP_RULES = r"""
valid(C, O, T, D) :- container(C), obstacle(O), tool(T), destination(D), needs(O, T).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in sorted(CONTAINERS):
        lines.append(asp.fact("container", cid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("needs", oid, obstacle.required_tool))
    for tid in sorted(TOOLS):
        lines.append(asp.fact("tool", tid))
    for did in sorted(DESTINATIONS):
        lines.append(asp.fact("destination", did))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    smoke_cases: list[StoryParams] = list(CURATED)
    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        smoke_cases.append(params)
    except Exception as err:
        rc = 1
        print(f"FAIL: resolve_params smoke test crashed: {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            _ = sample.to_json()
            if sample.world is None:
                raise StoryError("missing world")
            if sample.world.facts.get("delivered") is not True:
                raise StoryError("quest did not deliver")
            print(f"OK: smoke story {idx} generated.")
        except Exception as err:
            rc = 1
            print(f"FAIL: smoke story {idx} crashed: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale quest storyworld: a child carries root beer, an elder recalls a similar problem, and a flashback helps save the day."
    )
    ap.add_argument("--container", choices=sorted(CONTAINERS))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--destination", choices=sorted(DESTINATIONS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=["grandfather", "grandmother", "uncle", "aunt"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool and OBSTACLES[args.obstacle].required_tool != args.tool:
        raise StoryError(explain_rejection(args.obstacle, args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.container is None or combo[0] == args.container)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
        and (args.destination is None or combo[3] == args.destination)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    container_id, obstacle_id, tool_id, destination_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)

    elder_name = args.elder_name
    elder_type = args.elder_type
    if elder_name and not elder_type:
        elder_type = rng.choice(["grandfather", "grandmother", "uncle", "aunt"])
    if elder_type and not elder_name:
        candidates = [e["name"] for e in ELDERS if e["type"] == elder_type]
        elder_name = rng.choice(candidates)
    if not elder_name and not elder_type:
        elder_pick = rng.choice(ELDERS)
        elder_name = elder_pick["name"]
        elder_type = elder_pick["type"]

    return StoryParams(
        container=container_id,
        obstacle=obstacle_id,
        tool=tool_id,
        destination=destination_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")
    if params.elder_type not in {"grandfather", "grandmother", "uncle", "aunt"}:
        raise StoryError(f"(Unknown elder type: {params.elder_type})")
    if not valid_combo(params.container, params.obstacle, params.tool, params.destination):
        raise StoryError(explain_rejection(params.obstacle, params.tool))

    world = tell(
        container_cfg=CONTAINERS[params.container],
        obstacle_cfg=OBSTACLES[params.obstacle],
        tool_cfg=TOOLS[params.tool],
        destination_cfg=DESTINATIONS[params.destination],
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (container, obstacle, tool, destination) combos:\n")
        for container_id, obstacle_id, tool_id, destination_id in combos:
            print(f"  {container_id:7} {obstacle_id:7} {tool_id:6} {destination_id}")
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
            header = f"### {p.hero_name}: {p.container} over {p.obstacle} to {p.destination}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
